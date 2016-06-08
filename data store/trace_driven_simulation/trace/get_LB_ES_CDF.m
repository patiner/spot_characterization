function [LB, ES] = get_LB_ES_CDF(history,bid,T)

LB = length(find(history<=bid))/length(history)*T;

ES = mean(history(history<=bid));