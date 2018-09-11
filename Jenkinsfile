pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                echo 'Building..'
                bat '%repos%\\testgrounds\\appserverkiller.cmd' > nul 2> nul
                bat 'scripts\\install_package.cmd'
                bat '%repos%\\testgrounds\\appserverstarter.cmd'
            }
        }
        stage('Test') {
            steps {
                echo 'Testing..'
				bat 'python %repos%\\MATA030TESTSUITE.py'
				bat 'python %repos%\\MATA410TESTSUITE.py'
            }
        }
    }
}
