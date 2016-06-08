clear all;

load ./zone1/trace_1b.txt;
load ./zone2/trace_1d.txt;

figure;
hold on
plot(trace_1b, 'green', 'linewidth', 2);
plot(trace_1d, 'blue', 'linewidth', 2);

bid1 = ones(1440,1)*0.266;
bid2 = ones(1440,1)*0.266*5;

plot(bid1, 'r', 'linewidth', 2);
plot(bid2, 'r--', 'linewidth', 2);

legend('us-east-1c', 'us-east-1d', 'Bid1', 'Bid2');
xlabel('Time(minutes)');
ylabel('Price($)');
set(gca, 'fontsize', 20);
set(gca, 'fontweight', 'bold');
title('(a) Spot price');
box on