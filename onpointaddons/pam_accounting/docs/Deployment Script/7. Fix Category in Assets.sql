update pam_asset a
set category_id = 25
where a.coa_id in (
select z.coa_id
from pam_asset_category y
inner join pam_asset_reduction z on y.id = z.category_id
where y.id = 25
) and a.category_id <> 25
 
