from setuptools import setup
setup(
    name="tkencfs",
    version="0.8",
    description="EncFS GUI for encrypted directory mounting",
    url="https://github.com/biloucat/tkencfs",
    license="GPL-3.0",
    platforms="Archlinux",
    #py_modules=['tkencfs'],
    scripts=['tkencfs'],
    data_files=[('share/applications',['tkencfs.desktop']),('share/pixmaps',['tkencfs.png'])]
)