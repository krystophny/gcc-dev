! PR100194 - ICE in gfc_trans_create_temp_array with assumed-rank + contiguous
! { dg-do compile }
subroutine s(x)
   real :: x(..)
   call t(x)
contains
   subroutine t(y)
      real, contiguous :: y(..)
   end
end
