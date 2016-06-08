%% This script compute LB and ES under different window length. This result
%% two m*n matrix, LB_matrix and ES_matrix,where m is the bid size define 
%% in function get_LB_overestimate_new(), and n is the window length size. 

clear all;

path = './spot_traces/ec2_prices/us-east-1c/';
filename = 'price_time_m3.large.txt';
%dst_path = [path 'm3.large/'];
bid = 0.133;
BID_SIZE = 6;
% parts = {'(1-30)', '(31-60)', '(61-90)'};

price = load([path filename]);
price = price(1:129600,1);

% price_partition = [price(1:1440*30) price(1440*30+1:1440*30*2) price(1440*30*2+1:129600)];
window_length = [7 14 21 28];
figure_count = 1;


Lb_matrix = zeros(BID_SIZE, length(window_length));
ES_matrix = zeros(BID_SIZE, length(window_length));
min_values = zeros(BID_SIZE, 1);
min_index = zeros(BID_SIZE,1);

for i = 1:length(window_length)
    [Lb_matrix(:,i), ES_matrix(:,i)] = get_LB_overestimate_new(price, bid,window_length(i));
end



%------------------------plot Lb-----------------------------------
subplot(1,2,figure_count);
hold on
for i = 1:BID_SIZE
    [value, index] = min(Lb_matrix(i,:));
    min_values(i) = value;
    min_index(i) = window_length(index);
    plot(window_length, Lb_matrix(i,:))
end

plot(min_index, min_values, 'ro');


legend('bid = 0.1', 'bid = 0.5', 'bid = 1', 'bid = 2', 'bid = 5', 'bid = 10', 'min');
xlabel('window length');
ylabel('overestimation rate');
xlim([7 30]);
title('window length vs. Lb');
hold off
figure_count = figure_count + 1;




%-----------------------plot ES-------------------------------
min_values = zeros(BID_SIZE, 1);
min_index = zeros(BID_SIZE,1);

subplot(1,2,figure_count);
hold on
for i = 1:BID_SIZE
    [value, index] = min(ES_matrix(i,:));
    min_values(i) = value;
    min_index(i) = window_length(index);
    plot(window_length, ES_matrix(i,:))
end

plot(min_index, min_values, 'ro');


legend('bid = 0.1', 'bid = 0.5', 'bid = 1', 'bid = 2', 'bid = 5', 'bid = 10', 'min');
xlabel('window length');
ylabel('ES diff');
xlim([7 30]);
title('window length vs. Es');
hold off
figure_count = figure_count + 1;
