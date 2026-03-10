module avs_m

   type :: foo_t
   end type foo_t

   type, extends(foo_t) :: bar_t
      real, allocatable :: a
   end type bar_t

end module avs_m

program assign_vs_source

   use avs_m

   implicit none

   class(foo_t), allocatable :: foo(:)

   allocate(bar_t::foo(1))
   select type(foo)
   class is (bar_t)
      allocate(foo(1)%a)
   end select

   call check_assign(foo)

contains

   subroutine check_assign(f)

      class(foo_t), intent(in)  :: f(:)
      class(foo_t), allocatable :: g(:)

      g = f

      select type(g)
      class is (bar_t)
         print *,'is allocated?', allocated(g(1)%a)
      end select

      deallocate(g)
      allocate(g, SOURCE=f)

      select type(g)
      class is (bar_t)
         print *,'is allocated?', allocated(g(1)%a)
      end select

   end subroutine check_assign

end program assign_vs_source
