#!/bin/bash
for i in {0..31}
do
	convert -size 17x17 xc:transparent -draw "fill rgb($(($i * 20)), 10, $((160- $i * 5))) circle 8,8 8,0" "icon_$i.png"
done
