! PR 123868: Memory leak on assignment with nested allocatable components
! Regression introduced in commit 9636d90e4326003e6da1ea86df7c730852629920
! (deep copy semantics implementation)

module bugMod

  type :: vs
     character(len=1), allocatable :: s
  end type vs

  type :: ih
     type(vs), allocatable, dimension(:) :: hk
  end type ih

end module bugMod

program bugProg
  use bugMod

  block
    type(ih) :: c, d

    allocate(d%hk(1))
    allocate(d%hk(1)%s)
    d%hk(1)%s='z'
    c=d
    write (*,*) c%hk(1)%s,d%hk(1)%s

  end block

end program bugProg
