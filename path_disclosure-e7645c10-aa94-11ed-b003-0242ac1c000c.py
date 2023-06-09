import gc
import os

class _const:
    class ConstError(TypeError):
        pass

    def __setattr__(self, name, value):
        if self.__dict__.get(name):
            raise self.ConstError("Can't rebind const (%s)" % name)
        else:
            self.__dict__[name] = value

def is_folder(path):
    try:
        os.listdir(path)
        return True
    except:
        return False


def traverse(path):
    n = dict(name=path, children=[])
    for i in os.listdir(path):
        if is_folder(path + '/' + i):
            n['children'].append(traverse(path + '/' + i))
        else:
            n['children'].append(dict(name=i))
    return n

def config_path():
    try:
        return len(os.listdir('config'))
    except:
        os.mkdir('config')
    finally:
        return len(os.listdir('config'))


def rainbow(output, color=None):
    if color:
        if color == 'green':
            return '\033[1;32m%s\033[0m' % output
        if color == 'red':
            return '\033[1;31m%s\033[0m' % output
        if color == 'blue':
            return '\033[1;34m%s\033[0m' % output
    else:
        return output


def print_left_just(output, length=None):
    if length == None:
        length = len(output)
    return output + (length - len(output)) * ' '


def print_right_just(output, length):
    if length == None:
        length = len(output)
    return (length - len(output)) * ' ' + output


def print_as_a_list_item(index, title, subtile=None):
    index = ('[%s]' % str(index)).center(8).lstrip()
    title = print_left_just(rainbow(title, color='green'))
    if subtile:
        subtile = '\n' + len(index) * ' ' + subtile
    else:
        subtile = ''
    return index + title + subtile


def selection(hint, range):

    index = input(rainbow(hint, color='blue'))
    if int(index) > range or int(index) < 0:
        print(rainbow('out of range!', color='red'))
        selection(hint, range)
    else:
        return int(index)


def mem_analyze(func):
    """
    装饰器:内存分析
    """

    def wrapper(*args, **kwargs):
        memory_alloc = 'memory alloced: %s kb' % str(gc.mem_alloc() / 1024)
        memory_free = 'memory free: %s kb' % str(gc.mem_free() / 1024)
        gc.collect()
        memory_after_collect = 'after collect: %s kb available' % str(
            gc.mem_free() / 1024)
        print(rainbow(memory_alloc, color='red'))
        print(rainbow(memory_free, color='green'))
        print(rainbow(memory_after_collect, color='blue'))
        func(*args, **kwargs)
        memory_after_func_excute = 'after %s excuted: %s kb available' % (
            func.__name__, str(gc.mem_free() / 1024))
        print(rainbow(memory_after_func_excute, color='red'))

    return wrapper


