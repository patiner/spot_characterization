function [loss] = get_loss(hot_fail_prop, Mt_expand)

temp = sum(hot_fail_prop,2);

% for i = 1:24*60*90
%     %t = ceil(i/60);
%     temp(i) = temp(i)/Mt(i);    
% end

temp = temp./Mt_expand;

loss = temp(temp>0);
