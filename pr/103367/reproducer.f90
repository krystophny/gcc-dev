program p
   type t
      integer :: a(1,2) = 3
   end type
   type(t), parameter :: x(1) = t(4)
   integer :: y(1,2) = (x(b)%a)
   print *, y
end
