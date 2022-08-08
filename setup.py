import os
import sysconfig

from setuptools import setup
from setuptools.extension import Extension

PKG = "bpan"


def get_version():
    v = {}
    with open("src/_version.py") as fi:
        c = fi.read()
    exec(compile(c, "src/_version.py", "exec"), v)
    return v["__version__"]


def listdir(path):
    df = []
    for a, b, c in os.walk(path):
        if os.path.basename(a).startswith("__"):
            continue
        for i in c:
            if i.startswith("__"):
                continue
            p = os.path.join(a, i)
            df.append(p)
    return df


def getExtension():
    extensions = []
    for f in listdir("src"):
        e = Extension(PKG + "." + os.path.splitext(os.path.basename(f))[0],
                      [f, ], extra_compile_args=["-O3", ],)
        e.cython_directives = {
            'language_level': sysconfig._PY_VERSION_SHORT_NO_DOT[0]}
        extensions.append(e)
    return extensions


def getdes():
    des = ""
    with open(os.path.join(os.getcwd(), "README.md")) as fi:
        des = fi.read()
    return des


def get_requirement():
    requires = []
    with open(os.path.join(os.path.dirname(__file__), "requirements.txt")) as fi:
        for line in fi:
            line = line.strip()
            requires.append(line)
    return requires


setup(
    name=PKG,
    version=get_version(),
    packages=[PKG],
    license="MIT",
    url="https://github.com/yodeng/bpan",
    #package_dir={PKG: "src"},
    install_requires=get_requirement(),
    python_requires='>=3.7',
    ext_modules=getExtension(),
    long_description=getdes(),
    long_description_content_type='text/markdown',
    entry_points={
        'console_scripts': [
            '%s = %s.main:main' % (PKG.capitalize(), PKG),
            '%s = %s.main:main' % (PKG, PKG),
        ]
    }
)
