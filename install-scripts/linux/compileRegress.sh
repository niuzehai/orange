cd /home/orange/install-scripts
cvs update
chmod +x linux/testOrange.sh
chmod +x linux/compileRegress.sh

# prepare sources
cd /home/orange/daily
rm -Rf orange
rm -Rf test_install
cvs -Q -d :pserver:cvso@estelle.fri.uni-lj.si:/cvs checkout -d orange orange
cvs -Q -d :pserver:cvso@estelle.fri.uni-lj.si:/cvs checkout -d orange/source source
cp /home/orange/install-scripts/linux/setup.py /home/orange/daily/orange

# build
cd /home/orange/daily/orange
VER='1.test'
cat setup.py | sed s/"OrangeVer=\"ADDVERSION\""/"OrangeVer=\"Orange-$VER\""/ > new.py
mv -f new.py setup.py

echo `date` > ../output.log
if ! python setup.py compile >> ../output.log 2>&1 ; then
  cat compiling.log >> ../output.log
  mail -s "Linux: ERROR compiling Orange" janez.demsar@fri.uni-lj.si < ../output.log
  mail -s "Linux: ERROR compiling Orange" tomaz.curk@fri.uni-lj.si < ../output.log
  mail -s "Linux: ERROR compiling Orange" jurem@insilica.com < ../output.log
  cat ../output.log
  echo -e "\n\nERROR compiling, see log above"
  exit 1
fi

# install
cd /home/orange/daily/orange
echo `date` > install.log
if ! python setup.py install --orangepath=/home/orange/daily/test_install >> install.log 2>&1 ; then
  cat install.log >> ../output.log
  mail -s "Linux: ERROR installing Orange" tomaz.curk@fri.uni-lj.si < ../output.log
  mail -s "Linux: ERROR installing Orange" jurem@insilica.com < ../output.log
  cat ../output.log
  echo -e "\n\nERROR installing, see log above"
  exit 1
fi

# regression test
cd /home/orange/daily/orange
echo `date` > regress.log
if ! /home/orange/install-scripts/linux/testOrange.sh >> regress.log 2>&1 ; then
  cd /home/orange/daily/orange
  cat regress.log >> ../output.log
  mail -s "Linux: ERROR regression tests (compile and install OK) Orange" janez.demsar@fri.uni-lj.si < ../output.log
  mail -s "Linux: ERROR regression tests (compile and install OK) Orange" tomaz.curk@fri.uni-lj.si < ../output.log
  mail -s "Linux: ERROR regression tests (compile and install OK) Orange" jurem@insilica.com  < ../output.log
  cat ../output.log
  echo regression tests failed
else
  cd /home/orange/daily/orange
  cat regress.log >> ../output.log
  mail -s "Linux: Orange compiled successfully" tomaz.curk@fri.uni-lj.si < ../output.log
  mail -s "Linux: Orange compiled successfully" jurem@insilica.com < ../output.log
  cat ../output.log
  echo compiling was successful
fi

