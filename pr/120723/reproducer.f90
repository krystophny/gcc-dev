use openacc
implicit none (type, external)
integer, pointer :: a, b(:)
integer, allocatable :: c, d(:)

!$acc enter data attach(a)
!$acc enter data attach(b)
!$acc enter data attach(c)
!$acc enter data attach(d)

!$acc exit data detach(a)
!$acc exit data detach(b)
!$acc exit data detach(c)
!$acc exit data detach(d)
end
