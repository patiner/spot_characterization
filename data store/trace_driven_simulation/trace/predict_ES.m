function [ ES ] = predict_ES( ES_dist, D )
%PREDICT_LB Summary of this function goes here
%   Detailed explanation goes here

if ES_dist == 0
    ES = 0;
else
%     partition = 20;
%     edges = [0:D*24*60/partition:D*24*60];
% 
%     cdf = get_cdf(LB_dist, edges);
% 
%     X = rand;
%     index = find(cdf >= X, 1);
% 
%     LB = mean([edges(index - 1) edges(index)]);

    %5%ile
    
    
    ES = mean(ES_dist);

end



end

