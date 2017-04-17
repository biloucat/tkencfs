import sys
assert(sys.version_info[:2] >= (3,6))
import tkinter
assert(tkinter.TkVersion >= 8.6)
from setuptools import setup
setup(
    name="tkencfs",
    version="0.9",
    description="EncFS GUI for encrypted directory mounting",
    url="https://github.com/biloucat/tkencfs",
    license="GPL-3.0",
    platforms="Archlinux",
    #py_modules=['tkencfs'],
    scripts=['tkencfs'],
    data_files=[('share/applications',['tkencfs.desktop']),
                ('share/pixmaps',['tkencfs.png']),
                ('/usr/share/locale/fr/LC_MESSAGES',['i18n/fr/LC_MESSAGES/tkencfs.mo'])]
)