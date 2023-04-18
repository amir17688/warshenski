from cmd import Cmd

import wrapper
from objects import Project
from color import prnt, prnt_str, VIOLET, PURPLE, ORANGE, TURQ, BLUE
from cli_helpers import arglen, inject, state, emptystate, restrict, command
from cli_helpers import CmdError
import cli_helpers as cli
from state import CLIState


class TodoistCLI(Cmd):

    def __init__(self, conf):
        super().__init__()
        self.state = CLIState()
        self.conf = conf

    @command
    @arglen(0)
    @state
    def do_projects(self, args):
        """
        Retrieves a listing of all project names and their ids.

        Takes no arguments.
        """
        projects = wrapper.todoist.get_projects()
        cli.print_listing(projects, 0)
        return projects

    @command
    @arglen(0, 1)
    @inject
    @state
    def do_tasks(self, args):
        """
        Retrieves a listing of all tasks for the currently active project, if
        available. If there is no currently active project, simply lists all
        tasks across all projects.

        Takes an optional project name or id, only listing the tasks of the
        given project.
        """
        project_id = None
        if self.state.active_project:
            project_id = self.state.active_project.obj_id
        elif args:
            project_id = args[0]

        pos = 0
        if project_id:
            project = Project(project_id)
            prnt('<', project, '>', VIOLET, None, VIOLET)
            pos = cli.print_listing(project, pos)
            return project.tasks
        else:
            projects = wrapper.todoist.get_projects()
            tasks = []
            for project in projects:
                prnt('<', project, '>', VIOLET, None, VIOLET)
                pos = cli.print_listing(project, pos)
                tasks.extend(project.tasks)
            return tasks

    @command
    @arglen(2)
    @inject
    @restrict(['create', 'complete'])
    @emptystate
    def do_task(self, args):
        """
        Performs task operations.

        Takes the arguments (operations):
            1: create   <name> - Creates a task with the given name in the
                                 currently selected project.
            2: complete <id>   - Sets the task with the given id as completed.
        """
        sub_cmd = args[0]
        if sub_cmd == 'create':
            if self.state.active_project is None:
                raise CmdError("No active project. Use the select command")
            proj_id = self.state.active_project.obj_id
            wrapper.todoist.create_task(args[1], proj_id)
        elif sub_cmd == 'complete':
            wrapper.todoist.complete_task(args[1])

        self.do_tasks(str(self.state.active_project.obj_id))

    @command
    @arglen(1)
    @inject
    def do_select(self, args):
        """
        Sets the project with the given id as the currently selected project.

        All commands that implicitly act on a project with use this selected
        project. An example is task create.
        """
        try:
            self.state.set_project(int(args[0]))
            self.prompt = prnt_str(
                    '~',
                    '(', self.state.active_project.name, ')',
                    '>',
                    ' ',
                    PURPLE, TURQ, PURPLE, TURQ, BLUE, ORANGE
                    )
        except (ValueError, CmdError):
            raise CmdError("Argument must be a valid project")

    @command
    @arglen(2)
    @inject
    @restrict(['create', 'complete', 'clear', 'delete'])
    @emptystate
    def do_project(self, args):
        """
        Performs project operations.

        Takes the arguments (operations):
            1: create   <name> - Creates a project with the given name.
            2: complete <id>   - Sets all constituent tasks in the project with
                                 given id as completed.
            3: clear    <id>   - Delete all tasks in the project with the
                                 given id.
            4: delete   <id>   - Delete the project.
        """
        sub_cmd = args[0]
        if sub_cmd == 'create':
            wrapper.todoist.create_project(args[1])
        elif sub_cmd == 'complete':
            wrapper.todoist.complete_project(args[1])
        elif sub_cmd == 'clear':
            wrapper.todoist.clear_project(args[1])
        elif sub_cmd == 'delete':
            wrapper.todoist.delete_project(args[1])

    @command
    @arglen(0)
    @emptystate
    def do_exit(self, args):
        """
        Exits the CLI application.
        """
        prnt("Bye", VIOLET)
        exit(0)

    def precmd(self, line):
        cmds = self._decompose(line)
        if len(cmds) > 1:
            self.cmdqueue.extend(cmds[1:])
        return cmds[0]

    def _decompose(self, line):
        breakpoints = self._find_breakpoints(line)
        inclusive_breakpoints = [0] + breakpoints + [len(line)]
        cmds = []
        for i in range(len(breakpoints) + 1):
            start = inclusive_breakpoints[i]
            end = inclusive_breakpoints[i+1]
            cmd = line[start:end]
            if cmd and cmd[0] == ';':  # The first cmd fails this check
                cmd = cmd[1:]
            if cmd:  # Catch empty cmds from dud-EOL-semicolons
                cmds.append(cmd.strip())
        return cmds

    def _find_breakpoints(self, line):
        breakpoints = []
        in_quote = False
        for i, ch in enumerate(line):
            if ch in ["\"", "'"]:
                in_quote = not in_quote
            if ch == ';' and not in_quote:
                breakpoints.append(i)
            if ch == '#' and not in_quote:
                break  # This is comment territory, ignore everything.
        return breakpoints
