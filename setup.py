import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gradescope-todo-sync",
    version="0.0.1",
    author="Eric Lind",
    author_email="lamnoda3@gmail.com",
    description="An unofficial Gradescope API that syncs to Todoist",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ericlindcs/gradescope-calendar-sync",
    project_urls={
        "Homepage": "https://github.com/ericlindcs/gradescope-calendar-sync",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    install_requires=["requests", "bs4"],
)
