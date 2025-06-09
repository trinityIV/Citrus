from setuptools import setup, find_packages

setup(
    name='citrus',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask',
        'sqlalchemy',
        'pillow',
        'pytest',
        'pytest-cov'
    ],
    python_requires='>=3.8'
)
