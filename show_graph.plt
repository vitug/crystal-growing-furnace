set autoscale
#set xrange [:]
#set yrange [650:1070]
set xlabel "����� �� ������� ��������� (�������)"
set ylabel "����������� (�������)"
plot 'graph.dat' lt rgb "violet" with lines title "����������� ����������� �� ������� (����������� ����������)"
pause 60
#reload
load "show_graph.plt"