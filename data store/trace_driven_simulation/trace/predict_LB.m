function [ LB ] = predict_LB( LB_dist )
%PREDICT_LB Summary of this function goes here
%   Detailed explanation goes here

if LB_dist == 0
    LB = 0;
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
    
    
    LB = prctile(LB_dist,5);
    if LB > 1440
        LB = 1440;
    end
end



end

