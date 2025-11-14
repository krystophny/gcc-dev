! Comprehensive test for PR107721 - array constructor type-spec with parentheses
program test_comprehensive
  implicit none
  character :: x = 'a'

  print *, "=== INTEGER ==="
  print *, [integer ::  [1.0] ] **  2
  print *, [integer :: ([1.0])] **  2
  print *, [integer :: ((/1.0, 2.0/))] ** 2

  print *, "=== REAL ==="
  print *, [real ::  [2] ]   **  2
  print *, [real :: ([2])]   **  2
  print *, [real :: ((/2, 3/))] ** 2

  print *, "=== COMPLEX ==="
  print *, [complex ::  [3] ]   **  2
  print *, [complex :: ([3])]   **  2
  print *, [complex :: ((/3, 4/))] ** 2

  print *, "=== LOGICAL ==="
  print *, [logical :: [1], [0]]
  print *, [logical :: ([1]), ([0])]

  print *, "=== CHARACTER ==="
  print *, [character(4) :: x, 'b', 'c']
  print *, [character(4) :: (x), 'b', 'c']
  print *, [[character(4) :: x, 'b', 'c']]

  print *, "=== UNSIGNED (if supported) ==="
  ! Note: UNSIGNED may not be fully supported yet in gfortran

  print *, "=== Nested parentheses ==="
  print *, [real :: ((([2])))] ** 2
  print *, [integer :: (((([1.0]))))] ** 2

  print *, "=== SUCCESS ==="
end program test_comprehensive
