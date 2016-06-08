close all;
clear all;

load ./us-east-1c/m3.large_us_east_1c.txt;
load ./us-east-1d/m3.large_us_east_1d.txt;
pc = m3_large_us_east_1c(:,1);
pd = m3_large_us_east_1d(:,1);
p_od = 0.133;

T = 90*24; %hours

LB_OD_c = zeros(T,1);
LB_5OD_c = zeros(T,1);
ES_OD_c = zeros(T,1);
ES_5OD_c = zeros(T,1);

LB_OD_d = zeros(T,1);
LB_5OD_d = zeros(T,1);
ES_OD_d = zeros(T,1);
ES_5OD_d = zeros(T,1);

for t = 24*7+1:T
    if (t-1)*60+1440<=T*60
        trace_c = pc((t-1)*60+1:(t-1)*60+1440);
        trace_d = pd((t-1)*60+1:(t-1)*60+1440);
    else
        trace_c = pc((t-1)*60+1:T*60);
        trace_d = pd((t-1)*60+1:T*60);
    end
    [LB_OD_c(t), ES_OD_c(t)] = actual_LB_ES(trace_c,p_od);
    [LB_5OD_c(t), ES_5OD_c(t)] = actual_LB_ES(trace_c,5*p_od);
    
    [LB_OD_d(t), ES_OD_d(t)] = actual_LB_ES(trace_d,p_od);
    [LB_5OD_d(t), ES_5OD_d(t)] = actual_LB_ES(trace_d,5*p_od);
end

Lb_actual = [LB_OD_c LB_5OD_c LB_OD_d LB_5OD_d ones(T,1)*14400000];
ES_actual = [ES_OD_c ES_5OD_c ES_OD_d ES_5OD_d ones(T,1)*p_od];
save('Lb_actual.mat','Lb_actual');
save('ES_actual.mat','ES_actual');

% figure;
% plot(LB_OD_c)
% hold on;
% plot(LB_5OD_c,'r');
% hold off;
% 
% figure;
% plot(ES_OD_c)
% hold on;
% plot(ES_5OD_c,'r');
% hold off;
