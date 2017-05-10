for file in *.svg; do 
    echo $file
    inkscape -D -z --file=$file --export-pdf=`basename "$file" .svg`.pdf --export-latex
done
