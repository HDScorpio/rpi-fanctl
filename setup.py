from setuptools import setup

setup(
    name='rpi-fanctl',
    version='0.1.0',
    packages=['rpi_fanctl'],
    url='https://github.com/HDScorpio/rpi_fanctl',
    license='MIT',
    author='Andrey Ulagashev',
    author_email='ulagashev.andrey@gmail.com',
    description='Raspberry Pi fan control through GPIO',
    setup_requires=['setuptools'],
    install_requires=['RPi.GPIO'],
    entry_points={
        'console_scripts': [
            'rpi-fanctl = rpi_fanctl.main:main'
        ]
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: System :: Hardware',
        'Topic :: System :: Monitoring'
    ],
    keywords='raspberry fan'
)
