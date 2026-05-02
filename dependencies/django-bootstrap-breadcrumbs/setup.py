from setuptools import setup, find_packages

setup(
    name='django-bootstrap-breadcrumbs',
    version='0.9.2',
    author='Łukasz Mierzwa',
    author_email='l.mierzwa@gmail.com',
    description='Django breadcrumbs for Bootstrap 2, 3 or 4',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['Django'],
    zip_safe=False,
)
