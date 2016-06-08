close all;
clear all;

type = 'm3.xlarge';
region = 'us-west';
fname = ['./' type '/' region '-1a/' type '.txt'];
load(fname);
pc = m3_xlarge(:,1);
fname = ['./' type '/' region '-1c/' type '.txt'];
load(fname);
pd = m3_xlarge(:,1);
% load './m3.xlarge/us-east-1c/m3.xlarge.txt';
% load './m3.xlarge/us-east-1d/m3.xlarge.txt';


%us-east   m3l=0.133,   m3xl=0.266, c3l=0.105,  c32xl=0.42
%us-west oregon   m3l=0.133,   m3xl=0.266, c3l=0.105,  c32xl=0.42
p_od = 0.133;

T = 90*24; %hours

LB_OD_c = zeros(T,1)+1440;
LB_5OD_c = zeros(T,1)+1440;
ES_OD_c = zeros(T,1);
ES_5OD_c = zeros(T,1);

LB_OD_d = zeros(T,1)+1440;
LB_5OD_d = zeros(T,1)+1440;
ES_OD_d = zeros(T,1);
ES_5OD_d = zeros(T,1);

for t = 24*7+1:T
    
    trace_c = pc((t-1)*60-24*7*60+1:(t-1)*60); %past 7 days
%     LB_OD_c(t) = predict_LB(find_Lb(trace_c,p_od));
    ES_OD_c(t) = predict_ES(find_ES(trace_c,100));
   
%     LB_5OD_c(t) = predict_LB(find_Lb(trace_c,5*p_od));
    ES_5OD_c(t) = predict_ES(find_ES(trace_c,100));
    
    trace_d = pd((t-1)*60-24*7*60+1:(t-1)*60); %past 7 days
%     LB_OD_d(t) = predict_LB(find_Lb(trace_d,p_od));
    ES_OD_d(t) = predict_ES(find_ES(trace_d,100));
   
%     LB_5OD_d(t) = predict_LB(find_Lb(trace_d,5*p_od));
    ES_5OD_d(t) = predict_ES(find_ES(trace_d,100));
    
    
end

Lb_max = [LB_OD_c LB_5OD_c LB_OD_d LB_5OD_d ones(T,1)*14400000];
ES_max = [ES_OD_c ES_5OD_c ES_OD_d ES_5OD_d ones(T,1)*p_od];
fdir = ['./' type '/' region '/'];
save([fdir 'Lb_max.mat'],'Lb_max');
save([fdir 'ES_max.mat'],'ES_max');

% price = [pc(1:129600) pd(1:129600)];
% save([fdir 'price.mat'],'price');

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