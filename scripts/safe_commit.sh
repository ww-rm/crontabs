git commit -m $1
if [[ $? -eq 0 ]] || [[ $? -eq 1 ]]; then
    exit 0
else
    exit $?
fi