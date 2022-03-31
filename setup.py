from setuptools import setup


setup(
    name='cldfbench_baxterocrhymes',
    py_modules=['cldfbench_baxterocrhymes'],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'cldfbench.dataset': [
            'baxterocrhymes=cldfbench_baxterocrhymes:Dataset',
        ]
    },
    install_requires=[
        'cldfbench',
        'pylexibank',
    ],
    extras_require={
        'test': [
            'pytest-cldf',
        ],
    },
)
