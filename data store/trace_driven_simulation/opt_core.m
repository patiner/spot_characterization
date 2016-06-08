function [ core ] = opt_core( lambda, F )
%UNTITLED2 Summary of this function goes here
%   Detailed explanation goes here
% a1 = 4*1e-5;
% a0 = 0.7441;
% 
% core = ceil(a1*lambda+a0);

n = floor(lambda/max(F(:,1)));

core = n*max(F(:,2));

temp = lambda - n*max(F(:,1));

core = ceil(core + interp1(F(:,1),F(:,2),temp,'linear','extrap'));


end

