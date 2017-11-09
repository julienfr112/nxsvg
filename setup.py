from distutils.core import setup, Extension
setup(
    name="nxsvg", version="0.11pre",
    author="Yu Feng, Julien Fraichard",
    author_email="rainwoodman@gmail.com",
    description="Native SVG rendering of NetworkX Graphs",
    requires=["svgwrite"],
    package_dir={'nxsvg': 'src'},
    packages=['nxsvg'],
)
