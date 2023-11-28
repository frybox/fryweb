"""
扩展python import机制，直接import fry文件，在线转换成py文件，然后编译为.pyc文件直接执行。
"""
import sys
from importlib.machinery import FileFinder, SourceFileLoader
from importlib._bootstrap_external import _get_supported_file_loaders
from .generator import fry_to_py

# 最初.fry文件叫.pyx文件，参考.jsx，但.pyx在Cython中已经使用了，改为.fry文件
# 兼用期间，仍然支持.pyx文件的加载
PYXSOURCE_SUFFIXES = ['.fry', '.pyx']

class PyxSourceFileLoader(SourceFileLoader):
    def source_to_code(self, data, path, *, _optimize=-1):
        data = fry_to_py(data.decode(), path)
        return super(SourceFileLoader, self).source_to_code(data, path, _optimize=_optimize)

def install_path_hook():
    if sys.path_hooks and hasattr(sys.path_hooks[0], 'fryhcs'):
        return
    loader_details = [(PyxSourceFileLoader, PYXSOURCE_SUFFIXES)] + _get_supported_file_loaders()
    factory_func = FileFinder.path_hook(*loader_details)
    setattr(factory_func, 'fryhcs', True)
    sys.path_hooks.insert(0, factory_func)

    # 清空已有的PathEntryFinder缓存
    sys.path_importer_cache.clear()
