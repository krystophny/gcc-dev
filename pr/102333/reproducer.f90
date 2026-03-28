function f(x) result(y)
   class(*), pointer :: y
contains
   function g() result(z)
      procedure(f), pointer :: z
   end
end
