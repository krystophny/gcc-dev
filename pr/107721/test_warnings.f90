program test_warnings
  implicit none
  logical, dimension(2) :: larr
  character(4), dimension(3) :: charr
  character :: x = 'a'

  ! Test 1: LOGICAL array constructor with INTEGER literals
  print *, "Test 1: LOGICAL from INTEGER"
  larr = [logical :: [1], [0]]
  print *, larr

  ! Test 2: LOGICAL with parentheses
  print *, "Test 2: LOGICAL from INTEGER with parentheses"
  larr = [logical :: ([1]), ([0])]
  print *, larr

  ! Test 3: CHARACTER nested with different lengths
  print *, "Test 3: CHARACTER nested different lengths"
  charr = [[character(4) :: x, 'b', 'c']]
  print *, charr

end program test_warnings
