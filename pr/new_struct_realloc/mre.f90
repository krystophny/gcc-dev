module m
    use, intrinsic :: iso_fortran_env, only: dp => real64
    type :: t
        real(dp), allocatable :: c(:)
    end type
end module

program p
    use m
    type(t) :: s
    real(dp), allocatable :: w1(:,:,:), w2(:,:,:)
    integer :: i, iter

    do iter = 1, 3
        print *, iter
        allocate(s%c(8), w1(8,8,0:1), w2(8,8,0:1))
        !$acc enter data create(s%c, w1, w2)
        !$acc parallel loop present(w1, w2)
        do i = 1, 8
            w2(1,i,0) = w1(1,i,0)
        end do
        !$acc parallel loop present(w1, s%c)
        do i = 1, 8
            s%c(i) = w1(1,i,0)
        end do
        !$acc exit data delete(w1, w2, s%c)
        deallocate(w1, w2, s%c)
    end do
end program
