clear all;

OD_price = 0.266;

%==================== Execution time ====================
prop_exec = load('exec_time.txt');
prop_exec = prop_exec(:,2);
% OD1_exec = load('OD_1/exec_time.txt');

% figure;
% hold on
cdfplot(prop_exec);
% cdfplot(OD1_exec);
% legend('prop');
% hold off


%==================== Tput ===========================
% OD1_OD = load('OD_1/On-Demand.txt');
% OD1_OD = unique(OD1_OD, 'rows', 'stable');

prop_m1 = load('1b_0.266000.txt');
prop_m2 = load('1b_1.330000.txt');
prop_m3 = load('1d_0.266000.txt');
prop_m4 = load('1d_1.330000.txt');
prop_OD = load('On-Demand.txt');

prop_m1 = unique(prop_m1, 'rows', 'stable');
prop_m2 = unique(prop_m2, 'rows', 'stable');
prop_m3 = unique(prop_m3, 'rows', 'stable');
prop_m4 = unique(prop_m4, 'rows', 'stable');
prop_OD = unique(prop_OD, 'rows', 'stable');

% OD_tput =  length(OD1_exec) / OD1_OD(size(OD1_OD,1), 2);
prop_tput = length(prop_exec) / prop_OD(size(prop_OD,1),2);



%=================== Cost ============================
trace1 = load('zone1/trace_1b.txt');
trace2 = load('zone2/trace_1d.txt');

% OD1_cost = trapz(OD1_OD(:,2), OD1_OD(:,1)*(0.266*(12/3600)));

m1_cost = zeros(size(prop_m1,1),1);
m2_cost = zeros(size(prop_m1,1),1);
m3_cost = zeros(size(prop_m1,1),1);
m4_cost = zeros(size(prop_m1,1),1);

for i = 1:size(prop_m1,1)
    m1_cost(i) = prop_m1(i,1) * (trace1(min(floor(prop_m1(i,2)/5) + 1, 129600))*(12/3600));
    m2_cost(i) = prop_m2(i,1) * (trace1(min(floor(prop_m2(i,2)/5) + 1, 129600))*(12/3600));
    m3_cost(i) = prop_m3(i,1) * (trace2(min(floor(prop_m3(i,2)/5) + 1, 129600))*(12/3600));
    m4_cost(i) = prop_m4(i,1) * (trace2(min(floor(prop_m4(i,2)/5) + 1, 129600))*(12/3600));
end

m1_cost_total = trapz(prop_m1(:,2), m1_cost);
m2_cost_total = trapz(prop_m2(:,2), m2_cost);
m3_cost_total = trapz(prop_m3(:,2), m3_cost);
m4_cost_total = trapz(prop_m4(:,2), m4_cost);
od_cost_total = trapz(prop_OD(:,2), prop_OD(:,1)*(0.266*(12/3600)));

prop_cost = od_cost_total + ...
            m1_cost_total + ...
            m2_cost_total + ...
            m3_cost_total + ...
            m4_cost_total;
