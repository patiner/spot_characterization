function [LB, ES] = actual_LB_ES(trace,bid)

p_od = 0.133;
n = length(trace);

LB = find(trace>bid,1,'first')-1;
if isempty(LB)
    LB = n;
end
if LB > 0
    ES = mean(trace(1:LB));
else
    ES = 10*p_od;
end


