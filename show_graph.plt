set autoscale
#set xrange [:]
#set yrange [650:1070]
set xlabel "Время от запуска программы (секунды)"
set ylabel "Температура (градусы)"
plot 'graph.dat' lt rgb "violet" with lines title "Зависимость температуры от времени (обновляется ежеминутно)"
pause 60
#reload
load "show_graph.plt"