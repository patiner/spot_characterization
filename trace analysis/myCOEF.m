function [ coef ] = myCOEF( t1,t2,bid )
% corelation computed by formula (A and B) / (A or B)

AandB = 0;
AorB = 0;

for i = 1:length(t1)
    if (t1(i) > bid && t2(i) > bid)
        AandB = AandB + 1;
        AorB = AorB + 1;
    elseif (t1(i) > bid || t2(i) > bid)
        AorB = AorB + 1;
    end
end

if (AorB == 0)
    coef = 0;
else
    coef = AandB / AorB;
end
    
end

