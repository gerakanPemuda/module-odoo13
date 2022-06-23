-- Cek Balance
select b.code, b.name, b.parent_left, b.parent_right, a.ending_balance,
(
select SUM(x.ending_balance) 
from pam_balance_line x
inner join pam_coa y on y.id = x.coa_id
where y.transactional = true and y.id in (select id from pam_coa z where z.parent_left > b.parent_left and z.parent_right < b.parent_right) 
) as total_ending_balance
from pam_balance_line a
inner join pam_coa b on b.id = a.coa_id
where b.transactional = false
group by b.code, b.name, b.parent_left, b.parent_right, a.ending_balance
order by b.code


-- Update Balance
update pam_balance_line a
set
current_balance = coalesce((
select SUM(x.ending_balance) 
from pam_balance_line x
inner join pam_coa y on y.id = x.coa_id
where y.transactional = true and y.id in (select id from pam_coa z where z.parent_left > b.parent_left and z.parent_right < b.parent_right) 
),0),
ending_balance = current_balance
from pam_coa b 
where b.id = a.coa_id and b.transactional = false
