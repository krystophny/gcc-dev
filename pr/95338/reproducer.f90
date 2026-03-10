module m
contains
   function f(x)
      integer :: x
      integer :: f
      real :: g
      f = x
      return
   entry g(x)
      g = x
   end
end
program p
   use m
   print *, f(1)
   print *, g(1)
end
