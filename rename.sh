for file in output/*/*.xlsx; do
    dir=$(dirname "$file")
    base=$(basename "$dir")
    mv "$file" "output/${base}.xlsx"
    rm -rf "$dir"
    echo "moved $file to output/${base}.xlsx"
done