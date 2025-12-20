module bugMod

  type :: r
   contains
     procedure :: rma
     generic   :: assignment(=) => rma
  end type r

  type, extends(r) :: rm
     integer :: i
   contains
     final :: rmd
   end type rm

  interface rm
     module procedure rmc
  end interface rm

contains

  subroutine rmd(self)
    implicit none
    type(rm), intent(inout) :: self

    write (0,*) "type(rm) destructor called"
    return
  end subroutine rmd

  function rmc() result(self)
    implicit none
    type(rm) :: self

    write (0,*) "type(rm) constructor called"
    self%i=0
    return
  end function rmc

  subroutine rma(to,from)
    implicit none
    class(r), intent(  out) :: to
    class(r), intent(in   ) :: from

    write (0,*) "class(r) assignment(=) called"
    select type (to)
    type is (rm)
       select type (from)
       type is (rm)
          to%i=from%i
       end select
    end select
    return
  end subroutine rma

end module bugMod

program bugDestructFuncResult
  use bugMod
  implicit none

  block
    type(rm) :: i
    write (0,*) "construct our instance"
    i=rm()
    write (0,*) "finished"
  end block

end program bugDestructFuncResult
