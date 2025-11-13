program p
  print *, "*** Expect integer:"
  print *, [integer ::  [1.0] ] **  2
  print *, [integer :: ([1.0])] **  2
  print *, "*** Expect real:"
  print *, [real    ::  [2] ]   **  2
  print *, [real    :: ([2])]   **  2
  print *, "*** Expect complex:"
  print *, [complex ::  [3] ]   **  2
  print *, [complex :: ([3])]   **  2
end
