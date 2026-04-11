program p
   character(:), allocatable, target :: x
   logical :: l
   !$omp target map(from: l)
   l = allocated (x)
   !$omp end target
end
