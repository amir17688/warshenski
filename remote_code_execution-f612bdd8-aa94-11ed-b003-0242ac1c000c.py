# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import absolute_import, division, print_function, unicode_literals

import errno
import logging
import os
import re
import textwrap
from builtins import open
from collections import defaultdict
from contextlib import closing
from hashlib import sha1
from xml.etree import ElementTree

from future.utils import PY3, text_type

from pants.backend.jvm.subsystems.java import Java
from pants.backend.jvm.subsystems.jvm_platform import JvmPlatform
from pants.backend.jvm.subsystems.scala_platform import ScalaPlatform
from pants.backend.jvm.subsystems.zinc import Zinc
from pants.backend.jvm.targets.annotation_processor import AnnotationProcessor
from pants.backend.jvm.targets.javac_plugin import JavacPlugin
from pants.backend.jvm.targets.jvm_target import JvmTarget
from pants.backend.jvm.targets.scalac_plugin import ScalacPlugin
from pants.backend.jvm.tasks.classpath_util import ClasspathUtil
from pants.backend.jvm.tasks.jvm_compile.jvm_compile import JvmCompile
from pants.base.build_environment import get_buildroot
from pants.base.exceptions import TaskError
from pants.base.hash_utils import hash_file
from pants.base.workunit import WorkUnitLabel
from pants.engine.fs import DirectoryToMaterialize, PathGlobs, PathGlobsAndRoot
from pants.engine.isolated_process import ExecuteProcessRequest
from pants.java.distribution.distribution import DistributionLocator
from pants.util.contextutil import open_zip
from pants.util.dirutil import fast_relpath, safe_open
from pants.util.memo import memoized_method, memoized_property


# Well known metadata file required to register scalac plugins with nsc.
_SCALAC_PLUGIN_INFO_FILE = 'scalac-plugin.xml'

# Well known metadata file to register javac plugins.
_JAVAC_PLUGIN_INFO_FILE = 'META-INF/services/com.sun.source.util.Plugin'

# Well known metadata file to register annotation processors with a java 1.6+ compiler.
_PROCESSOR_INFO_FILE = 'META-INF/services/javax.annotation.processing.Processor'


logger = logging.getLogger(__name__)


class BaseZincCompile(JvmCompile):
  """An abstract base class for zinc compilation tasks."""

  _name = 'zinc'

  @staticmethod
  def _write_scalac_plugin_info(resources_dir, scalac_plugin_target):
    scalac_plugin_info_file = os.path.join(resources_dir, _SCALAC_PLUGIN_INFO_FILE)
    with safe_open(scalac_plugin_info_file, 'w') as f:
      f.write(textwrap.dedent("""
        <plugin>
          <name>{}</name>
          <classname>{}</classname>
        </plugin>
      """.format(scalac_plugin_target.plugin, scalac_plugin_target.classname)).strip())

  @staticmethod
  def _write_javac_plugin_info(resources_dir, javac_plugin_target):
    javac_plugin_info_file = os.path.join(resources_dir, _JAVAC_PLUGIN_INFO_FILE)
    with safe_open(javac_plugin_info_file, 'w') as f:
      classname = javac_plugin_target.classname if PY3 else javac_plugin_target.classname.decode('utf-8')
      f.write(classname)

  @staticmethod
  def validate_arguments(log, whitelisted_args, args):
    """Validate that all arguments match whitelisted regexes."""
    valid_patterns = {re.compile(p): v for p, v in whitelisted_args.items()}

    def validate(idx):
      arg = args[idx]
      for pattern, has_argument in valid_patterns.items():
        if pattern.match(arg):
          return 2 if has_argument else 1
      log.warn("Zinc argument '{}' is not supported, and is subject to change/removal!".format(arg))
      return 1

    arg_index = 0
    while arg_index < len(args):
      arg_index += validate(arg_index)

  @staticmethod
  def _get_zinc_arguments(settings):
    """Extracts and formats the zinc arguments given in the jvm platform settings.

    This is responsible for the symbol substitution which replaces $JAVA_HOME with the path to an
    appropriate jvm distribution.

    :param settings: The jvm platform settings from which to extract the arguments.
    :type settings: :class:`JvmPlatformSettings`
    """
    zinc_args = [
      '-C-source', '-C{}'.format(settings.source_level),
      '-C-target', '-C{}'.format(settings.target_level),
    ]
    if settings.args:
      settings_args = settings.args
      if any('$JAVA_HOME' in a for a in settings.args):
        try:
          distribution = JvmPlatform.preferred_jvm_distribution([settings], strict=True)
        except DistributionLocator.Error:
          distribution = JvmPlatform.preferred_jvm_distribution([settings], strict=False)
        logger.debug('Substituting "$JAVA_HOME" with "{}" in jvm-platform args.'
                     .format(distribution.home))
        settings_args = (a.replace('$JAVA_HOME', distribution.home) for a in settings.args)
      zinc_args.extend(settings_args)
    return zinc_args

  @classmethod
  def implementation_version(cls):
    return super(BaseZincCompile, cls).implementation_version() + [('BaseZincCompile', 7)]

  @classmethod
  def get_jvm_options_default(cls, bootstrap_option_values):
    return ('-Dfile.encoding=UTF-8', '-Dzinc.analysis.cache.limit=1000',
            '-Djava.awt.headless=true', '-Xmx2g')

  @classmethod
  def get_args_default(cls, bootstrap_option_values):
    return ('-C-encoding', '-CUTF-8', '-S-encoding', '-SUTF-8', '-S-g:vars')

  @classmethod
  def get_warning_args_default(cls):
    return ('-C-deprecation', '-C-Xlint:all', '-C-Xlint:-serial', '-C-Xlint:-path',
            '-S-deprecation', '-S-unchecked', '-S-Xlint')

  @classmethod
  def get_no_warning_args_default(cls):
    return ('-C-nowarn', '-C-Xlint:none', '-S-nowarn', '-S-Xlint:none', )

  @classmethod
  def get_fatal_warnings_enabled_args_default(cls):
    return ('-S-Xfatal-warnings', '-C-Werror')

  @classmethod
  def get_fatal_warnings_disabled_args_default(cls):
    return ()

  @classmethod
  def register_options(cls, register):
    super(BaseZincCompile, cls).register_options(register)
    register('--whitelisted-args', advanced=True, type=dict,
             default={
               '-S.*': False,
               '-C.*': False,
               '-file-filter': True,
               '-msg-filter': True,
               },
             help='A dict of option regexes that make up pants\' supported API for zinc. '
                  'Options not listed here are subject to change/removal. The value of the dict '
                  'indicates that an option accepts an argument.')

    register('--incremental', advanced=True, type=bool, default=True,
             help='When set, zinc will use sub-target incremental compilation, which dramatically '
                  'improves compile performance while changing large targets. When unset, '
                  'changed targets will be compiled with an empty output directory, as if after '
                  'running clean-all.')

    register('--incremental-caching', advanced=True, type=bool,
             help='When set, the results of incremental compiles will be written to the cache. '
                  'This is unset by default, because it is generally a good precaution to cache '
                  'only clean/cold builds.')

  @classmethod
  def subsystem_dependencies(cls):
    return super(BaseZincCompile, cls).subsystem_dependencies() + (Zinc.Factory, JvmPlatform,)

  @classmethod
  def prepare(cls, options, round_manager):
    super(BaseZincCompile, cls).prepare(options, round_manager)
    ScalaPlatform.prepare_tools(round_manager)

  @property
  def incremental(self):
    """Zinc implements incremental compilation.

    Setting this property causes the task infrastructure to clone the previous
    results_dir for a target into the new results_dir for a target.
    """
    return self.get_options().incremental

  @property
  def cache_incremental(self):
    """Optionally write the results of incremental compiles to the cache."""
    return self.get_options().incremental_caching

  @memoized_property
  def _zinc(self):
    return Zinc.Factory.global_instance().create(self.context.products)

  def __init__(self, *args, **kwargs):
    super(BaseZincCompile, self).__init__(*args, **kwargs)
    # A directory to contain per-target subdirectories with apt processor info files.
    self._processor_info_dir = os.path.join(self.workdir, 'apt-processor-info')

    # Validate zinc options.
    ZincCompile.validate_arguments(self.context.log, self.get_options().whitelisted_args,
                                   self._args)
    if self.execution_strategy == self.HERMETIC:
      try:
        fast_relpath(self.get_options().pants_workdir, get_buildroot())
      except ValueError:
        raise TaskError(
          "Hermetic zinc execution currently requires the workdir to be a child of the buildroot "
          "but workdir was {} and buildroot was {}".format(
            self.get_options().pants_workdir,
            get_buildroot(),
          )
        )

      if self.get_options().use_classpath_jars:
        # TODO: Make this work by capturing the correct DirectoryDigest and passing them around the
        # right places.
        # See https://github.com/pantsbuild/pants/issues/6432
        raise TaskError("Hermetic zinc execution currently doesn't work with classpath jars")

  def select(self, target):
    raise NotImplementedError()

  def select_source(self, source_file_path):
    raise NotImplementedError()

  def register_extra_products_from_contexts(self, targets, compile_contexts):
    compile_contexts = [self.select_runtime_context(compile_contexts[t]) for t in targets]
    zinc_analysis = self.context.products.get_data('zinc_analysis')
    zinc_args = self.context.products.get_data('zinc_args')

    if zinc_analysis is not None:
      for compile_context in compile_contexts:
        zinc_analysis[compile_context.target] = (compile_context.classes_dir,
        compile_context.jar_file,
        compile_context.analysis_file)

    if zinc_args is not None:
      for compile_context in compile_contexts:
        with open(compile_context.zinc_args_file, 'r') as fp:
          args = fp.read().split()
        zinc_args[compile_context.target] = args

  def create_empty_extra_products(self):
    if self.context.products.is_required_data('zinc_analysis'):
      self.context.products.safe_create_data('zinc_analysis', dict)

    if self.context.products.is_required_data('zinc_args'):
      self.context.products.safe_create_data('zinc_args', lambda: defaultdict(list))

  def javac_classpath(self):
    # Note that if this classpath is empty then Zinc will automatically use the javac from
    # the JDK it was invoked with.
    return Java.global_javac_classpath(self.context.products)

  def scalac_classpath(self):
    return ScalaPlatform.global_instance().compiler_classpath(self.context.products)

  def write_extra_resources(self, compile_context):
    """Override write_extra_resources to produce plugin and annotation processor files."""
    target = compile_context.target
    if isinstance(target, ScalacPlugin):
      self._write_scalac_plugin_info(compile_context.classes_dir, target)
    elif isinstance(target, JavacPlugin):
      self._write_javac_plugin_info(compile_context.classes_dir, target)
    elif isinstance(target, AnnotationProcessor) and target.processors:
      processor_info_file = os.path.join(compile_context.classes_dir, _PROCESSOR_INFO_FILE)
      self._write_processor_info(processor_info_file, target.processors)

  def _write_processor_info(self, processor_info_file, processors):
    with safe_open(processor_info_file, 'w') as f:
      for processor in processors:
        f.write('{}\n'.format(processor.strip()))

  @memoized_property
  def _zinc_cache_dir(self):
    """A directory where zinc can store compiled copies of the `compiler-bridge`.

    The compiler-bridge is specific to each scala version, and is lazily computed by zinc if the
    appropriate version does not exist. Eventually it would be great to just fetch this rather
    than compiling it.
    """
    hasher = sha1()
    for cp_entry in [self._zinc.zinc, self._zinc.compiler_interface, self._zinc.compiler_bridge]:
      hasher.update(os.path.relpath(cp_entry, self.get_options().pants_workdir))
    key = hasher.hexdigest()[:12]
    return os.path.join(self.get_options().pants_bootstrapdir, 'zinc', key)

  def compile(self, ctx, args, dependency_classpath, upstream_analysis,
              settings, compiler_option_sets, zinc_file_manager,
              javac_plugin_map, scalac_plugin_map):
    absolute_classpath = (ctx.classes_dir,) + tuple(ce.path for ce in dependency_classpath)

    if self.get_options().capture_classpath:
      self._record_compile_classpath(absolute_classpath, ctx.target, ctx.classes_dir)

    # TODO: Allow use of absolute classpath entries with hermetic execution,
    # specifically by using .jdk dir for Distributions:
    # https://github.com/pantsbuild/pants/issues/6430
    self._verify_zinc_classpath(absolute_classpath, allow_dist=(self.execution_strategy != self.HERMETIC))
    # TODO: Investigate upstream_analysis for hermetic compiles
    self._verify_zinc_classpath(upstream_analysis.keys())

    def relative_to_exec_root(path):
      # TODO: Support workdirs not nested under buildroot by path-rewriting.
      return fast_relpath(path, get_buildroot())

    scala_path = self.scalac_classpath()
    compiler_interface = self._zinc.compiler_interface
    compiler_bridge = self._zinc.compiler_bridge
    classes_dir = ctx.classes_dir
    analysis_cache = ctx.analysis_file

    scala_path = tuple(relative_to_exec_root(c) for c in scala_path)
    compiler_interface = relative_to_exec_root(compiler_interface)
    compiler_bridge = relative_to_exec_root(compiler_bridge)
    analysis_cache = relative_to_exec_root(analysis_cache)
    classes_dir = relative_to_exec_root(classes_dir)
    # TODO: Have these produced correctly, rather than having to relativize them here
    relative_classpath = tuple(relative_to_exec_root(c) for c in absolute_classpath)

    zinc_args = []
    zinc_args.extend([
      '-log-level', self.get_options().level,
      '-analysis-cache', analysis_cache,
      '-classpath', ':'.join(relative_classpath),
      '-d', classes_dir,
    ])
    if not self.get_options().colors:
      zinc_args.append('-no-color')

    zinc_args.extend(['-compiler-interface', compiler_interface])
    zinc_args.extend(['-compiler-bridge', compiler_bridge])
    # TODO: Kill zinc-cache-dir: https://github.com/pantsbuild/pants/issues/6155
    # But for now, this will probably fail remotely because the homedir probably doesn't exist.
    zinc_args.extend(['-zinc-cache-dir', self._zinc_cache_dir])
    zinc_args.extend(['-scala-path', ':'.join(scala_path)])

    zinc_args.extend(self._javac_plugin_args(javac_plugin_map))
    # Search for scalac plugins on the classpath.
    # Note that:
    # - We also search in the extra scalac plugin dependencies, if specified.
    # - In scala 2.11 and up, the plugin's classpath element can be a dir, but for 2.10 it must be
    #   a jar.  So in-repo plugins will only work with 2.10 if --use-classpath-jars is true.
    # - We exclude our own classes_dir/jar_file, because if we're a plugin ourselves, then our
    #   classes_dir doesn't have scalac-plugin.xml yet, and we don't want that fact to get
    #   memoized (which in practice will only happen if this plugin uses some other plugin, thus
    #   triggering the plugin search mechanism, which does the memoizing).
    scalac_plugin_search_classpath = (
      (set(absolute_classpath) | set(self.scalac_plugin_classpath_elements())) -
      {ctx.classes_dir, ctx.jar_file}
    )
    zinc_args.extend(self._scalac_plugin_args(scalac_plugin_map, scalac_plugin_search_classpath))
    if upstream_analysis:
      zinc_args.extend(['-analysis-map',
                        ','.join('{}:{}'.format(
                          relative_to_exec_root(k),
                          relative_to_exec_root(v)
                        ) for k, v in upstream_analysis.items())])

    zinc_args.extend(self._zinc.rebase_map_args)

    zinc_args.extend(args)
    zinc_args.extend(self._get_zinc_arguments(settings))
    zinc_args.append('-transactional')

    for option_set in compiler_option_sets:
      enabled_args = self.get_options().compiler_option_sets_enabled_args.get(option_set, [])
      if option_set == 'fatal_warnings':
        enabled_args = self.get_options().fatal_warnings_enabled_args
      zinc_args.extend(enabled_args)

    for option_set, disabled_args in self.get_options().compiler_option_sets_disabled_args.items():
      if option_set not in compiler_option_sets:
        if option_set == 'fatal_warnings':
          disabled_args = self.get_options().fatal_warnings_disabled_args
        zinc_args.extend(disabled_args)

    if not self._clear_invalid_analysis:
      zinc_args.append('-no-clear-invalid-analysis')

    if not zinc_file_manager:
      zinc_args.append('-no-zinc-file-manager')

    jvm_options = []

    if self.javac_classpath():
      # Make the custom javac classpath the first thing on the bootclasspath, to ensure that
      # it's the one javax.tools.ToolProvider.getSystemJavaCompiler() loads.
      # It will probably be loaded even on the regular classpath: If not found on the bootclasspath,
      # getSystemJavaCompiler() constructs a classloader that loads from the JDK's tools.jar.
      # That classloader will first delegate to its parent classloader, which will search the
      # regular classpath.  However it's harder to guarantee that our javac will preceed any others
      # on the classpath, so it's safer to prefix it to the bootclasspath.
      jvm_options.extend(['-Xbootclasspath/p:{}'.format(':'.join(self.javac_classpath()))])

    jvm_options.extend(self._jvm_options)

    zinc_args.extend(ctx.sources)

    self.log_zinc_file(ctx.analysis_file)
    with open(ctx.zinc_args_file, 'wb') as fp:
      for arg in zinc_args:
        fp.write(arg)
        fp.write(b'\n')

    if self.execution_strategy == self.HERMETIC:
      zinc_relpath = fast_relpath(self._zinc.zinc, get_buildroot())

      snapshots = [
        self._zinc.snapshot(self.context._scheduler),
        ctx.target.sources_snapshot(self.context._scheduler),
      ]

      directory_digests = tuple(
        entry.directory_digest for entry in dependency_classpath if entry.directory_digest
      )
      if len(directory_digests) != len(dependency_classpath):
        for dep in dependency_classpath:
          if dep.directory_digest is None:
            logger.warning(
              "ClasspathEntry {} didn't have a DirectoryDigest, so won't be present for hermetic "
              "execution".format(dep)
            )

      if scala_path:
        # TODO: ScalaPlatform._tool_classpath should capture this and memoize it.
        # See https://github.com/pantsbuild/pants/issues/6435
        snapshots.append(
          self.context._scheduler.capture_snapshots((PathGlobsAndRoot(
            PathGlobs(scala_path),
            get_buildroot(),
          ),))[0]
        )

      merged_input_digest = self.context._scheduler.merge_directories(
        tuple(s.directory_digest for s in (snapshots)) + directory_digests
      )

      # TODO: Extract something common from Executor._create_command to make the command line
      # TODO: Lean on distribution for the bin/java appending here
      argv = tuple(['.jdk/bin/java'] + jvm_options + ['-cp', zinc_relpath, Zinc.ZINC_COMPILE_MAIN] + zinc_args)
      req = ExecuteProcessRequest(
        argv=argv,
        input_files=merged_input_digest,
        output_files=(analysis_cache,),
        output_directories=(classes_dir,),
        description="zinc compile for {}".format(ctx.target.address.spec),
        # TODO: These should always be unicodes
        jdk_home=text_type(self._zinc.dist.home),
      )
      res = self.context.execute_process_synchronously(req, self.name(), [WorkUnitLabel.COMPILER])
      # TODO: Materialize as a batch in do_compile or somewhere
      self.context._scheduler.materialize_directories((
        DirectoryToMaterialize(get_buildroot(), res.output_directory_digest),
      ))

      # TODO: This should probably return a ClasspathEntry rather than a DirectoryDigest
      return res.output_directory_digest
    else:
      if self.runjava(classpath=[self._zinc.zinc],
                      main=Zinc.ZINC_COMPILE_MAIN,
                      jvm_options=jvm_options,
                      args=zinc_args,
                      workunit_name=self.name(),
                      workunit_labels=[WorkUnitLabel.COMPILER],
                      dist=self._zinc.dist):
        raise TaskError('Zinc compile failed.')

  def _verify_zinc_classpath(self, classpath, allow_dist=True):
    def is_outside(path, putative_parent):
      return os.path.relpath(path, putative_parent).startswith(os.pardir)

    dist = self._zinc.dist
    for path in classpath:
      if not os.path.isabs(path):
        raise TaskError('Classpath entries provided to zinc should be absolute. '
                        '{} is not.'.format(path))

      if is_outside(path, self.get_options().pants_workdir) and (not allow_dist or is_outside(path, dist.home)):
        raise TaskError('Classpath entries provided to zinc should be in working directory or '
                        'part of the JDK. {} is not.'.format(path))
      if path != os.path.normpath(path):
        raise TaskError('Classpath entries provided to zinc should be normalized '
                        '(i.e. without ".." and "."). {} is not.'.format(path))

  def log_zinc_file(self, analysis_file):
    self.context.log.debug('Calling zinc on: {} ({})'
                           .format(analysis_file,
                                   hash_file(analysis_file).upper()
                                   if os.path.exists(analysis_file)
                                   else 'nonexistent'))

  @classmethod
  def _javac_plugin_args(cls, javac_plugin_map):
    ret = []
    for plugin, args in javac_plugin_map.items():
      for arg in args:
        if ' ' in arg:
          # Note: Args are separated by spaces, and there is no way to escape embedded spaces, as
          # javac's Main does a simple split on these strings.
          raise TaskError('javac plugin args must not contain spaces '
                          '(arg {} for plugin {})'.format(arg, plugin))
      ret.append('-C-Xplugin:{} {}'.format(plugin, ' '.join(args)))
    return ret

  def _scalac_plugin_args(self, scalac_plugin_map, classpath):
    if not scalac_plugin_map:
      return []

    plugin_jar_map = self._find_scalac_plugins(list(scalac_plugin_map.keys()), classpath)
    ret = []
    for name, cp_entries in plugin_jar_map.items():
      # Note that the first element in cp_entries is the one containing the plugin's metadata,
      # meaning that this is the plugin that will be loaded, even if there happen to be other
      # plugins in the list of entries (e.g., because this plugin depends on another plugin).
      ret.append('-S-Xplugin:{}'.format(':'.join(cp_entries)))
      for arg in scalac_plugin_map[name]:
        ret.append('-S-P:{}:{}'.format(name, arg))
    return ret

  def _find_scalac_plugins(self, scalac_plugins, classpath):
    """Returns a map from plugin name to list of plugin classpath entries.

    The first entry in each list is the classpath entry containing the plugin metadata.
    The rest are the internal transitive deps of the plugin.

    This allows us to have in-repo plugins with dependencies (unlike javac, scalac doesn't load
    plugins or their deps from the regular classpath, so we have to provide these entries
    separately, in the -Xplugin: flag).

    Note that we don't currently support external plugins with dependencies, as we can't know which
    external classpath elements are required, and we'd have to put the entire external classpath
    on each -Xplugin: flag, which seems excessive.
    Instead, external plugins should be published as "fat jars" (which appears to be the norm,
    since SBT doesn't support plugins with dependencies anyway).
    """
    # Allow multiple flags and also comma-separated values in a single flag.
    plugin_names = {p for val in scalac_plugins for p in val.split(',')}
    if not plugin_names:
      return {}

    active_plugins = {}
    buildroot = get_buildroot()

    cp_product = self.context.products.get_data('runtime_classpath')
    for classpath_element in classpath:
      name = self._maybe_get_plugin_name(classpath_element)
      if name in plugin_names:
        plugin_target_closure = self._plugin_targets('scalac').get(name, [])
        # It's important to use relative paths, as the compiler flags get embedded in the zinc
        # analysis file, and we port those between systems via the artifact cache.
        rel_classpath_elements = [
          os.path.relpath(cpe, buildroot) for cpe in
          ClasspathUtil.internal_classpath(plugin_target_closure, cp_product, self._confs)]
        # If the plugin is external then rel_classpath_elements will be empty, so we take
        # just the external jar itself.
        rel_classpath_elements = rel_classpath_elements or [classpath_element]
        # Some classpath elements may be repeated, so we allow for that here.
        if active_plugins.get(name, rel_classpath_elements) != rel_classpath_elements:
          raise TaskError('Plugin {} defined in {} and in {}'.format(name, active_plugins[name],
                                                                     classpath_element))
        active_plugins[name] = rel_classpath_elements
        if len(active_plugins) == len(plugin_names):
          # We've found all the plugins, so return now to spare us from processing
          # of the rest of the classpath for no reason.
          return active_plugins

    # If we get here we must have unresolved plugins.
    unresolved_plugins = plugin_names - set(active_plugins.keys())
    raise TaskError('Could not find requested plugins: {}'.format(list(unresolved_plugins)))

  @classmethod
  @memoized_method
  def _maybe_get_plugin_name(cls, classpath_element):
    """If classpath_element is a scalac plugin, returns its name.

    Returns None otherwise.
    """
    def process_info_file(cp_elem, info_file):
      plugin_info = ElementTree.parse(info_file).getroot()
      if plugin_info.tag != 'plugin':
        raise TaskError('File {} in {} is not a valid scalac plugin descriptor'.format(
            _SCALAC_PLUGIN_INFO_FILE, cp_elem))
      return plugin_info.find('name').text

    if os.path.isdir(classpath_element):
      try:
        with open(os.path.join(classpath_element, _SCALAC_PLUGIN_INFO_FILE), 'r') as plugin_info_file:
          return process_info_file(classpath_element, plugin_info_file)
      except IOError as e:
        if e.errno != errno.ENOENT:
          raise
    else:
      with open_zip(classpath_element, 'r') as jarfile:
        try:
          with closing(jarfile.open(_SCALAC_PLUGIN_INFO_FILE, 'r')) as plugin_info_file:
            return process_info_file(classpath_element, plugin_info_file)
        except KeyError:
          pass
    return None


class ZincCompile(BaseZincCompile):
  """Compile Scala and Java code to classfiles using Zinc."""

  @classmethod
  def product_types(cls):
    return ['runtime_classpath', 'zinc_analysis', 'zinc_args']

  def select(self, target):
    # Require that targets are marked for JVM compilation, to differentiate from
    # targets owned by the scalajs contrib module.
    if not isinstance(target, JvmTarget):
      return False
    return target.has_sources('.java') or target.has_sources('.scala')

  def select_source(self, source_file_path):
    return source_file_path.endswith('.java') or source_file_path.endswith('.scala')

  def execute(self):
    if JvmPlatform.global_instance().get_options().compiler == 'zinc':
      return super(ZincCompile, self).execute()
