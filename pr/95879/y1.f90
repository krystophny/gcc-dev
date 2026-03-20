module m
contains
   integer function f(x) bind(c)
      use iso_c_binding
      c_funloc(f) = x
   end
end
