..\env\Scripts\python -m unittest discover -s . -p "test_*"
git push
..\env\Scripts\python setup.py bdist_egg upload