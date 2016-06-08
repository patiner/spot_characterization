close all;
clear all;

load ../Mt_expand.mat;

load ./m3.large/us-east/opt_CDF.mat;
loss_m3l_CDF_east = get_loss(hot_fail_prop, Mt_expand);

load ./m3.large/us-east/opt_prop_new.mat;
loss_m3l_prop_east = get_loss(hot_fail_prop, Mt_expand);

load ./m3.xlarge/us-east/opt_CDF.mat;
loss_m3xl_CDF_east = get_loss(hot_fail_prop, Mt_expand);

load ./m3.xlarge/us-east/opt_prop_new.mat;
loss_m3xl_prop_east = get_loss(hot_fail_prop, Mt_expand);

load ./c3.large/us-east/opt_CDF.mat;
loss_c3l_CDF_east = get_loss(hot_fail_prop, Mt_expand);

load ./c3.large/us-east/opt_prop_new.mat;
loss_c3l_prop_east = get_loss(hot_fail_prop, Mt_expand);

load ./c3.2xlarge/us-east/opt_CDF.mat;
loss_c32xl_CDF_east = get_loss(hot_fail_prop, Mt_expand);

load ./c3.2xlarge/us-east/opt_prop_new.mat;
loss_c32xl_prop_east = get_loss(hot_fail_prop, Mt_expand);

load ./m3.large/us-west/opt_CDF.mat;
loss_m3l_CDF_west = get_loss(hot_fail_prop, Mt_expand);

load ./m3.large/us-west/opt_prop_new.mat;
loss_m3l_prop_west = get_loss(hot_fail_prop, Mt_expand);

load ./m3.xlarge/us-west/opt_CDF.mat;
loss_m3xl_CDF_west = get_loss(hot_fail_prop, Mt_expand);

load ./m3.xlarge/us-west/opt_prop_new.mat;
loss_m3xl_prop_west = get_loss(hot_fail_prop, Mt_expand);

load ./c3.large/us-west/opt_CDF.mat;
loss_c3l_CDF_west = get_loss(hot_fail_prop, Mt_expand(1:129581));

load ./c3.large/us-west/opt_prop_new.mat;
loss_c3l_prop_west = get_loss(hot_fail_prop, Mt_expand(1:129581));

load ./c3.2xlarge/us-west/opt_CDF.mat;
loss_c32xl_CDF_west = get_loss(hot_fail_prop, Mt_expand);

load ./c3.2xlarge/us-west/opt_prop_new.mat;
loss_c32xl_prop_west = get_loss(hot_fail_prop, Mt_expand);

% length(loss_m3l_CDF_east)
% % mean(loss_m3l_CDF_east)
% length(loss_m3l_CDF_west)
% % mean(loss_m3l_CDF_west)
% length(loss_m3l_prop_east)
% % mean(loss_m3l_prop_east)
% length(loss_m3l_prop_west)
% % mean(loss_m3l_prop_west)

figure;
subplot(2,1,1);
hist(loss_c32xl_CDF_east,20);
legend('BL-CDF');
ylabel('frequency');
axis([0 1 0 4]);
title('Histogram of data loss (%) for c3.2xl us-east');
subplot(2,1,2);
hist(loss_c32xl_prop_east,20);
legend('PROP');
ylabel('frequency');
xlabel('Data loss (%)');
axis([0 1 0 4]);
