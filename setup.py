from setuptools import setup, find_packages

metadata = {}
with open("configwebui/__metadata__.py", "r", encoding="utf-8") as f:
    exec(f.read(), metadata)

setup(
    version=metadata["__version__"],
    url=metadata["__url__"],
    description=metadata["__description__"],
    keywords=", ".join(metadata["__keywords__"]),
    packages=find_packages(),
    install_requires=metadata["__dependencies__"],
    include_package_data=True,
)
