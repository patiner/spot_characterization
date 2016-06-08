%% History window for correlation
%% This script return a m*n matrix, named COEF_matrix, where m is bid size
%% and n is window length size. The ij cell store correlation computed by
%% corresponding functions (e.g. myCOEF, corrcoef) under given bid and 
%% window size.

clear all;

path1 = './spot_traces/ec2_prices/us-east-1c/';
path2 = './spot_traces/ec2_prices/us-east-1d/';
filename = 'price_time_c3.large.txt';
OD_price = 0.105;
bid = [OD_price*0.5 OD_price OD_price*5];  % bids
BID_SIZE = length(bid);

tmp = load([path1 filename]);
price(:,1) = tmp(1:129600,1);
tmp = load([path2 filename]);
price(:,2) = tmp(1:129600,1);



window_length = [3 7 14 21 28];  % window lengths
figure_count = 1;


COEF_matrix = zeros(BID_SIZE, length(window_length)); % result
min_values = zeros(BID_SIZE, 1);
min_index = zeros(BID_SIZE,1);


for i = 1:length(window_length)
    for j = 1:BID_SIZE
        coef_pred = zeros(129600-window_length(i)*1440-1440,1);
        coef_real = zeros(129600-window_length(i)*1440-1440,1);
        
        for k = 1:129600-window_length(i)*1440-1440
            % To get result computed bu corrcoef, change myCOEF to corrcoef
            coef_pred(k) = myCOEF(price(k:k+window_length(i)*1440,1),...
                                  price(k:k+window_length(i)*1440,2),...
                                  bid(j));
                              
            coef_real(k) = myCOEF(price(k+window_length(i)*1440:k+window_length(i)*1440+1440,1), ...
                                  price(k+window_length(i)*1440:k+window_length(i)*1440+1440,2), ...
                                  bid(j));
        end
        
        underestimate = find(coef_pred < coef_real);
        COEF_matrix(j,i) = length(underestimate) / length(coef_real);
    end
end




