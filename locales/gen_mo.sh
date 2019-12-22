BASEDIR=$(dirname "$0")
cd $BASEDIR
find . -name \*.po -execdir sh -c 'msgfmt "$0" -o `basename $0 .po`.mo' '{}' \;